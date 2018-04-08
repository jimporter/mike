import mimetypes
import posixpath
import stat
from six.moves import BaseHTTPServer
from six.moves.urllib import parse as urlparse

from . import git_utils
from .app_version import version


def _to_git_path(path):
    path = posixpath.normpath(urlparse.urlsplit(path).path)
    return path[1:]


class GitBranchHTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    server_version = "MikeHTTP/" + version

    # Note: Set this in a subclass!
    branch = None

    def do_HEAD(self):
        self.send_headers()

    def do_GET(self):
        path = self.send_headers()
        if path is not None:
            body = git_utils.read_file(self.branch, path)
            self.wfile.write(body)

    def send_headers(self):
        path = _to_git_path(self.path)
        try:
            if stat.S_ISDIR(git_utils.file_mode(self.branch, path)):
                url = urlparse.urlsplit(self.path)
                if not url.path.endswith('/'):
                    # Redirect the browser to a URL with a slash at the end,
                    # like Apache.
                    self.send_response(301)
                    dest = urlparse.urlunsplit(
                        url[:2] + (url[2] + '/',) + url[3:]
                    )
                    self.send_header('Location', dest)
                    self.end_headers()
                    return

                path = posixpath.join(path, 'index.html')
                git_utils.file_mode(self.branch, path)

            self.send_response(200)
            self.send_header('Content-Type', self.guess_type(path))
            self.end_headers()

            return path
        except git_utils.GitError:
            self.send_error(404, 'File not found')
        except Exception:  # pragma: no cover
            self.send_error(500, 'Internal server error')

    def guess_type(self, path):
        base, ext = posixpath.splitext(path)
        if not mimetypes.inited:
            mimetypes.init()
        return mimetypes.types_map.get(ext, 'application/octet-stream')
