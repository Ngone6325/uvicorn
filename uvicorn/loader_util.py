import os
from pathlib import Path
from typing import Type, List, TextIO, Any, Dict

import yaml
from yaml import SequenceNode, ScalarNode


class Loader(yaml.Loader):
    def __init__(self, stream):
        self.stream = stream
        super(Loader, self).__init__(self.stream)

    def apply_path_include(self, node) -> Any:
        root = os.path.split(self.stream.name)[0]
        filename = os.path.join(root, self.construct_scalar(node))
        with open(filename, 'r') as f:
            return yaml.load(f, Loader)

    def apply_join_string(self, node: SequenceNode) -> str:
        if not isinstance(node, SequenceNode):
            raise f"node must be an instance of SequenceNode, not {type(node)}"
        if node.value.__len__() != 2:
            raise (f"the length of node.value must be eq 2, and the first element is a concat string, "
                   f"the second element is a ScalarNode list")
        if not isinstance(node.value[0].value, str):
            raise "the first element should be a concat string"
        if not isinstance(node.value[1].value, list):
            raise "the second element should be a ScalarNode list"

        contact_string_node: SequenceNode = node.value[0]
        string_node_list: List[ScalarNode] = node.value[1].value
        return contact_string_node.value.join([self.construct_scalar(x) for x in string_node_list])

    def apply_concat_string(self, node: SequenceNode) -> str:
        if not isinstance(node, SequenceNode):
            raise f"node must be an instance of SequenceNode, not {type(node)}"
        return ''.join([self.construct_scalar(x) for x in node.value])

    def apply_join_path(self, node: SequenceNode) -> Path:
        if not isinstance(node, SequenceNode):
            raise f"node must be an instance of SequenceNode, not {type(node)}"
        if len(node.value) < 2:
            raise (f"the length of node.value must be eq 2, and the first element is a concat string, "
                   f"the second element is a ScalarNode list")
        root_path: Path = Path(node.value[0].value)
        return root_path.joinpath(*[self.construct_scalar(x) for x in node.value[1:]])

    def apply_join_workspace(self, node: SequenceNode) -> Path:
        return Path(__file__).cwd().joinpath(node.value)


class LoaderUtil:

    @staticmethod
    def yaml_loader() -> Type[Loader]:
        Loader.add_constructor('!include', Loader.apply_path_include)
        Loader.add_constructor('!join', Loader.apply_join_string)
        Loader.add_constructor('!concat', Loader.apply_concat_string)
        Loader.add_constructor('!joinpath', Loader.apply_join_path)
        Loader.add_constructor('!workspace', Loader.apply_join_workspace)
        return Loader

    @staticmethod
    def unsafe_load(config: str | TextIO) -> Dict[str, Any]:
        return yaml.load(config, Loader=LoaderUtil.yaml_loader())
