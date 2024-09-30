import yaml
from jinja2 import Environment, FileSystemLoader
import subprocess
import argparse
import json

def deploy_services(config_file, template_file):
    # Load the configuration from config.yaml
    with open(config_file, 'r') as f:
        config_data = yaml.safe_load(f)

    # Set up Jinja2 environment and load the template
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template(template_file)

    # Get the specified namespace from the configuration
    namespace = config_data['namespace']

    # Check if the namespace exists
    try:
        subprocess.run(["kubectl", "get", "namespace", namespace], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        # Namespace does not exist, create it
        print(f"Namespace '{namespace}' does not exist. Creating it...")
        subprocess.run(["kubectl", "create", "namespace", namespace], check=True)

    # Render the entire manifest template
    rendered_manifest = template.render(namespace=namespace)

    # Split template into separate manifests based on `---` separator
    manifests = rendered_manifest.split('---')

    for manifest in manifests:
        if manifest.strip():  # Ensure the manifest is not empty
            # Save the rendered manifest to a temporary file
            with open('temp_manifest.yaml', 'w') as temp_file:
                temp_file.write(manifest)

            # Apply the rendered manifest to Kubernetes
            subprocess.run(["kubectl", "apply", "-f", "temp_manifest.yaml", "-n", namespace], check=True)

    # Scale deployments after applying the manifests
    for service_name, service_config in config_data['services'].items():
        desired_replicas = service_config.get('replicas', 1)

        # Scale the deployment using kubectl scale command
        print(f"Scaling '{service_name}' to {desired_replicas} replicas...")
        subprocess.run(["kubectl", "scale", "deployment", service_name, f"--replicas={desired_replicas}", "-n", namespace], check=True)

    # Optional: Clean up the temporary manifest file after deployment
    subprocess.run(["rm", "temp_manifest.yaml"])

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Deploy services using a template and configuration file.')
    parser.add_argument('config_file', type=str, help='Path to the config.yaml file')
    parser.add_argument('template_file', type=str, help='Path to the deployment_template.yaml file')

    args = parser.parse_args()

    # Call the deploy_services function with provided arguments
    deploy_services(args.config_file, args.template_file)
