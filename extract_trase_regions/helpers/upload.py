import subprocess
import sys
from extract_trase_regions.helpers.yaml import parse_yaml

ALLOWED_ENVIRONMENTS = {"production", "staging", "review"}


def upload_to_s3(environment_key):
    if environment_key not in ALLOWED_ENVIRONMENTS:
        raise ValueError(
            f"Invalid environment: {environment_key}. "
            f"Must be one of {ALLOWED_ENVIRONMENTS}"
        )
    
    secrets = parse_yaml("extract_trase_regions/secrets.yml")
    environment = secrets["environments"][environment_key]
    s3_bucket = environment["s3_bucket"]
    distribution_id = environment["distribution_id"]
    
    commands = [
        f'aws s3 sync ./data/ s3://{s3_bucket}/data/trase-regions/ --exclude ".DS_Store"',
        f'aws cloudfront create-invalidation --distribution-id {distribution_id} --paths "/data/trase-regions/*"',
    ]

    for cmd in commands:
        print(f"---> running: {cmd}")
        subprocess.run(cmd, shell=True, check=True)


def main():
    if len(sys.argv) != 2:
        print("Usage: upload-trase <environment>")
        print(f"Environments: {', '.join(sorted(ALLOWED_ENVIRONMENTS))}")
        sys.exit(1)
    
    upload_to_s3(sys.argv[1])


if __name__ == "__main__":
    main()