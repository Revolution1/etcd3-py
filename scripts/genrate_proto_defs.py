"""
Use this script to generate swagger api definition from etcd's .proto files

reference:
    https://github.com/grpc-ecosystem/grpc-gateway
    https://github.com/gogo/protobuf

First you need a golang environment and install protobuf (protoc)
    For MacOS just run `brew install go protobuf`

Then you need to download/compile some dependencies:
    go get -u github.com/grpc-ecosystem/grpc-gateway/protoc-gen-grpc-gateway
    go get -u github.com/grpc-ecosystem/grpc-gateway/protoc-gen-swagger
    go get -u github.com/golang/protobuf/protoc-gen-go

    go get -u github.com/gogo/protobuf/proto
    go get -u github.com/gogo/protobuf/jsonpb
    go get -u github.com/gogo/protobuf/protoc-gen-gogo
    go get -u github.com/gogo/protobuf/gogoproto

    go get -u go.etcd.io/etcd

Find proto files that defines GRPC-Gateway endpoints
    find $GOPATH/src/go.etcd.io/etcd -name '*.proto' |xargs grep -r 'post: "/v3' | cut -d ':' -f 1|uniq

"""
import sys

import json
import os
import shutil

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import six
import tempfile
import glob

import re
from semantic_version import Version
from subprocess import CalledProcessError, check_call, check_output


def do_cmd(cmd, err='Error'):
    print('>>>', cmd)
    try:
        return check_call(cmd, shell=True)
    except CalledProcessError:
        sys.exit(err)


def do_out(cmd):
    return check_output(cmd, shell=True)


GEN_CMD = '''protoc -I=$GOPATH/src/go.etcd.io/ \
    -I=$GOPATH/src/github.com/gogo/protobuf \
    -I/usr/local/include -I. \
    -I$GOPATH/src \
    -I$GOPATH/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis \
    --swagger_out={out} {proto}'''

PROTOS = (
    (
        '3.0.x',
        (
            'etcdserver/etcdserverpb/rpc.proto',
        )
    ),
    (
        '3.1.x',
        (
            'etcdserver/etcdserverpb/rpc.proto',
        )
    ),
    (
        '3.2.x',
        (
            'etcdserver/etcdserverpb/rpc.proto',
            'etcdserver/api/v3lock/v3lockpb/v3lock.proto',
            'etcdserver/api/v3election/v3electionpb/v3election.proto'
        )
    ),
    (
        '3.3.x',
        (
            'etcdserver/etcdserverpb/rpc.proto',
            'etcdserver/api/v3lock/v3lockpb/v3lock.proto',
            'etcdserver/api/v3election/v3electionpb/v3election.proto'
        )
    ),
)

GOPATH = os.getenv('GOPATH')

ETCD_PATH = os.path.join(GOPATH, 'src/go.etcd.io/etcd')

TAGS = do_out('cd %s;git tag -l' % ETCD_PATH)
if six.PY3:
    TAGS = six.text_type(TAGS, encoding='utf-8')


def find_newest_version(pattern, tags=TAGS):
    p = pattern.replace('.', r'\.').replace('x', r'\d+')
    r = re.compile(p)
    versions = r.findall(tags)
    return max(versions, key=lambda v: Version(v))


DEFS_DIR = os.path.join(os.path.dirname(__file__), '../etcd3/protodefs')

outs = []
init = ['import re\n',
        'PROTOS = []\n']
for v, files in PROTOS:
    do_cmd('cd %s; git checkout v%s' % (ETCD_PATH, find_newest_version(v)))
    vname = 'v' + v.replace('.', '_')
    spec_name = 'spec_' + vname
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_dir = os.path.join(DEFS_DIR, vname)
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)
        for f in files:
            absf = os.path.join(ETCD_PATH, f)
            do_cmd(GEN_CMD.format(out=tmp_dir, proto=absf))
        for f in do_out("find %s -name '*.json'" % tmp_dir).strip().splitlines():
            if six.PY3:
                f = six.text_type(f, encoding='utf-8')
            shutil.copy(f, out_dir)
        jsons = glob.glob(os.path.join(out_dir, './*.json'))
        with open(os.path.join(out_dir, '__init__.py'), 'w') as f:
            f.write('%s = %s\n' % (spec_name, repr({
                'consumes': ['application/json'],
                'definitions': {},
                'info': {'title': 'etcd api v' + v,
                         'version': v},
                'paths': {},
                'produces': ['application/json'],
                'schemes': ['http', 'https'],
                'swagger': '2.0'}
            )))
            for j in jsons:
                name = os.path.basename(j).replace('.', '_')
                with open(j) as jf:
                    spec = json.load(jf)
                f.write('%s = %s\n' % (name, repr(spec)))
                f.write(
                    "{spec_name}['paths'].update({name}.get('paths', {{}}))\n{spec_name}['definitions'].update({name}.get('definitions', {{}}))\n".format(
                        spec_name=spec_name, name=name))
    init.append('from .%s import %s\n' % (vname, spec_name))
    init.append("PROTOS.append(('%s', %s))\n" % (v, spec_name))
with open(os.path.join(DEFS_DIR, '__init__.py'), 'w') as f:
    f.write('\n'.join(init))
    f.write('\n')
    f.write("""\
def get_proto(server_version):
    p = server_version.replace('.', r'\.').replace('x', r'\d+')
    r = re.compile(p)
    for v, spec in PROTOS:
        if r.match(v):
            return spec
    if PROTOS:
        return PROTOS[-1][-1] # return the newest by default
""")
