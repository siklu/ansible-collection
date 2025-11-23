.PHONY: test-all test-command test-config test-facts build install

# Build and install collection
build:
	ansible-galaxy collection build --force

install: build
	ansible-galaxy collection install siklu-eh-1.0.0.tar.gz --force

# Run all tests
test-all: test-command test-config test-facts

# Individual test targets
test-command:
	ansible-playbook test_command.yaml -i inventory.ini -v

test-config:
	ansible-playbook test_config.yaml -i inventory.ini -v

test-facts:
	ansible-playbook test_facts.yaml -i inventory.ini -v

# Clean build artifacts
clean:
	rm -f siklu-eh-*.tar.gz
	rm -rf ~/.ansible/collections/ansible_collections/siklu/eh

# Full rebuild and test
rebuild: clean install test-all
