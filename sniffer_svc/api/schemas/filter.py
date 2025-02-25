from pydantic import BaseModel


class Filter(BaseModel):
    filter: str
    proto: str

    def get_as_bpf(self):
        return "berkley packet filter" + self.filter + self.proto


