from litestar.handlers import ASGIRouteHandler

if not hasattr(ASGIRouteHandler, "resolve_request_max_body_size"):
    """Adding missing ASGIRouteHandler.resolve_request_max_body_size method for compatibility of sqladmin and litestar"""


    def _resolve_request_max_body_size(self):
        return None


    ASGIRouteHandler.resolve_request_max_body_size = _resolve_request_max_body_size
