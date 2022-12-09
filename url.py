class URL:
    secure: bool
    hostname: str
    resource: str

    def __init__(self, url: str):
        self.parse_url(url)

    def parse_url(self, url: str):
        if url.startswith("https://"):
            self.secure = True
        else:
            self.secure = False

        if url.startswith("https://") or url.startswith("http://"):
            index = url.find("//")
            url = url[index + 2::]

        fs_i = url.find('/')
        """ first slash index """

        if fs_i != -1:
            self.hostname = url[:fs_i]
            self.resource = url[fs_i::]
        else:
            self.hostname = url
            self.resource = "/"

    def __repr__(self):
        out = f"Secure: {self.secure}\n" \
              f"Hostname: {self.hostname}\n" \
              f"Resource: {self.resource}"
        return out
