import yaml


def parse_yaml(file_path):
    with open(file_path) as f:
        try:
            return yaml.load(f, Loader=yaml.FullLoader)
        except Exception as e:
            raise e
