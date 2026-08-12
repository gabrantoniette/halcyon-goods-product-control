"""Translation of the API's HTTP responses into a single shape used by the client.

Every call to the server goes through `try_response`, which always returns the
same structure - success flag, status code, human-readable message and data - so
that the terminal menu and the web front-end handle errors the same way.
"""

import requests as r

# Explains the reason behind each HTTP status code a request may return
STATUS_CODE_MESSAGES = {
    200: "OK - The request was processed successfully.",
    201: "Created - The resource was created successfully.",
    204: "No Content - The request succeeded but there is no content to return.",
    400: "Bad Request - The request has invalid syntax or parameters.",
    401: "Unauthorized - Authentication is missing or invalid for this resource.",
    403: "Forbidden - Access to the requested resource was denied.",
    404: "Not Found - The requested resource or product was not found.",
    405: "Method Not Allowed - The HTTP method is not allowed for this endpoint.",
    408: "Request Timeout - The server took too long to receive the request.",
    409: "Conflict - The request conflicts with the current state of the resource.",
    422: "Unprocessable Entity - The submitted data failed validation (e.g. invalid body/fields).",
    429: "Too Many Requests - The number of requests exceeded the allowed limit.",
    500: "Internal Server Error - An unexpected error occurred on the server.",
    502: "Bad Gateway - An invalid response was received from an upstream server.",
    503: "Service Unavailable - The server is temporarily unavailable.",
    504: "Gateway Timeout - The upstream server did not respond in time.",
}


def describe_status(status_code):
    return STATUS_CODE_MESSAGES.get(
        status_code, f"Status code {status_code} is not mapped."
    )


def read_body(response):
    """Return the response body, or None when it is not valid JSON."""
    try:
        return response.json()
    except ValueError:
        return None


def detail_of(body):
    """Extract the error message FastAPI sends in the 'detail' field."""
    if isinstance(body, dict):
        return body.get("detail")
    return None


def try_response(response):
    try:
        response.raise_for_status()
    except r.HTTPError as e:
        body = read_body(response)
        return {
            "success": False,
            "status_code": response.status_code,
            "message": f"Request failed: {e} | {describe_status(response.status_code)}",
            "detail": detail_of(body),
            "data": body,
        }
    except r.RequestException as e:
        return {
            "success": False,
            "status_code": None,
            "message": f"Could not reach the API: {e}",
            "detail": None,
            "data": None,
        }
    else:
        return {
            "success": True,
            "status_code": response.status_code,
            "message": describe_status(response.status_code),
            "detail": None,
            "data": read_body(response),
        }
