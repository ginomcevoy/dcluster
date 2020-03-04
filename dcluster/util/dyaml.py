import yaml


class DumpWithIndent(yaml.Dumper):

    def increase_indent(self, flow=False, indentless=False):
        return super(DumpWithIndent, self).increase_indent(flow, False)


def dump_with_offset_indent(entries, offset_indents):

    class DumpWithOffsetIndent(DumpWithIndent):

        def __init__(self, *args, **kwargs):
            super(DumpWithOffsetIndent, self).__init__(*args, **kwargs)
            for _ in range(0, offset_indents):
                self.increase_indent(False, False)

    return yaml.dump(entries, Dumper=DumpWithOffsetIndent, default_flow_style=False)


def dump(entries):
    return yaml.dump(entries, default_flow_style=False)


def dump_with_indent(entries):
    return yaml.dump(entries, Dumper=DumpWithIndent, default_flow_style=False)


def dump_to_filepath(entries, filepath):

    with open(filepath, 'w') as f:
        yaml.dump(entries, f, Dumper=DumpWithIndent, default_flow_style=False)


if __name__ == '__main__':
    foo = {
        'name': 'foo',
        'my_list': [
            {'foo': 'test', 'bar': 'test2'},
            {'foo': 'test3', 'bar': 'test4'}],
        'hello': 'world',
    }
    print(dump(foo))
    print(dump_with_indent(foo))
    print(dump_with_offset_indent(foo, 1))
    print(dump_with_offset_indent(foo, 2))
    print(dump_with_offset_indent(foo, 3))
