try:
    from beans.BaseDo import BaseDo
except ModuleNotFoundError:
    from webkit_layer.python.beans.BaseDo import BaseDo


class CodeStructureDo(BaseDo):
    def __init__(self, id=None, s3_key=None, structure=None, source=None, **kwargs):
        super().__init__(**kwargs)
        self.id = id
        self.s3_key = s3_key
        self.structure = structure
        self.source = source
