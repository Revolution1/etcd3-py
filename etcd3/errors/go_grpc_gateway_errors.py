from .go_grpc_codes import GRPCCode as codes
from .go_net_http_status import HTTPStatus as http


def HTTPStatusFromCode(code):
    """
    HTTPStatusFromCode converts a gRPC error code into the corresponding HTTP response status.
    """
    if code == codes.OK:
        return http.StatusOK
    elif code == codes.Canceled:
        return http.StatusRequestTimeout
    elif code == codes.Unknown:
        return http.StatusInternalServerError
    elif code == codes.InvalidArgument:
        return http.StatusBadRequest
    elif code == codes.DeadlineExceeded:
        return http.StatusRequestTimeout
    elif code == codes.NotFound:
        return http.StatusNotFound
    elif code == codes.AlreadyExists:
        return http.StatusConflict
    elif code == codes.PermissionDenied:
        return http.StatusForbidden
    elif code == codes.Unauthenticated:
        return http.StatusUnauthorized
    elif code == codes.ResourceExhausted:
        return http.StatusForbidden
    elif code == codes.FailedPrecondition:
        return http.StatusPreconditionFailed
    elif code == codes.Aborted:
        return http.StatusConflict
    elif code == codes.OutOfRange:
        return http.StatusBadRequest
    elif code == codes.Unimplemented:
        return http.StatusNotImplemented
    elif code == codes.Internal:
        return http.StatusInternalServerError
    elif code == codes.Unavailable:
        return http.StatusServiceUnavailable
    elif code == codes.DataLoss:
        return http.StatusInternalServerError
    else:
        return http.StatusInternalServerError
