import subprocess
import json
import sys


def run_kubectl_command(command):
    """Run a kubectl command and return the output."""
    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}\n{e.stderr}")
        sys.exit(1)


def get_all_nodes():
    """Get the list of all nodes in the Kubernetes cluster."""
    command = ["kubectl", "get", "nodes", "-o", "json"]
    output = run_kubectl_command(command)
    nodes = json.loads(output)
    return [node['metadata']['name'] for node in nodes['items']]


def add_label_to_node(node_name, label):
    """Add a label to the specified node."""
    command = ["kubectl", "label", "node", node_name, label, "--overwrite"]
    print(f"Labeling node {node_name} with {label}...")
    run_kubectl_command(command)
    print(f"Label {label} added to node {node_name} successfully.")


def main(label, node_names=None, node_count=None):
    if node_names:
        # Add label to the specified nodes
        for node_name in node_names:
            add_label_to_node(node_name, label)
    else:
        # Fetch the node list and label the specified number of nodes
        all_nodes = get_all_nodes()
        if not node_count or node_count > len(all_nodes):
            print(f"Error: Node count exceeds the number of available nodes ({len(all_nodes)} available).")
            sys.exit(1)

        selected_nodes = all_nodes[:node_count]
        for node_name in selected_nodes:
            add_label_to_node(node_name, label)


if __name__ == "__main__":
    # Example usage: python add_k8s_label.py "mylabel=value" --names "node1,node2"
    # or: python add_k8s_label.py "mylabel=value" --count 3
    import argparse

    parser = argparse.ArgumentParser(description="Add a label to Kubernetes nodes.")
    parser.add_argument("label", help="The label to add (e.g., key=value)")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--names", help="Comma-separated list of node names to add the label to")
    group.add_argument("--count", type=int, help="Number of nodes to label in order")

    args = parser.parse_args()

    if args.names:
        node_names = args.names.split(',')
        main(args.label, node_names=node_names)
    else:
        main(args.label, node_count=args.count)

