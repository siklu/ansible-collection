.PHONY: help install build clean test-unit test-integration test-config test-set-commands test-rollback test-all rebuild

help:
	@echo "Siklu EH Ansible Collection - Available targets:"
	@echo "  make install              - Build and install collection"
	@echo "  make build                - Build collection tarball"
	@echo "  make clean                - Remove build artifacts"
	@echo "  make test-unit            - Run unit tests (pytest)"
	@echo "  make test-integration     - Run facts integration tests"
	@echo "  make test-config          - Run config module integration tests (IP/routes via module)"
	@echo "  make test-set-commands    - Run set command integration tests (direct CLI commands)"
	@echo "  make test-rollback        - Run rollback protection integration tests"
	@echo "  make test-all             - Run all tests (unit + all integration)"
	@echo "  make rebuild              - Clean, install, and test"

# Build collection
build:
	ansible-galaxy collection build --force

# Install collection
install: build
	ansible-galaxy collection install siklu-eh-*.tar.gz --force

# Run unit tests
test-unit:
	@echo "Running unit tests..."
	pytest tests/unit/ -v

# Run facts integration tests
test-integration:
	@echo "Running facts integration tests..."
	ansible-playbook test_facts.yaml -i inventory.ini -v

# Run config module integration tests (IP/routes via siklu_config module)
test-config:
	@echo "Running config module integration tests..."
	ansible-playbook test_config.yaml -i inventory.ini -v

# Run set command integration tests (direct set ip/set route commands)
test-set-commands:
	@echo "Running set command integration tests..."
	ansible-playbook test_set_commands.yaml -i inventory.ini -v

# Run rollback integration tests
test-rollback:
	@echo "Running rollback protection integration tests..."
	ansible-playbook test_rollback.yaml -i inventory.ini -v

# Run all tests
test-all: test-unit test-integration test-config test-set-commands test-rollback
	@echo "All tests completed!"

# Clean build artifacts
clean:
	rm -f siklu-eh-*.tar.gz
	rm -rf ~/.ansible/collections/ansible_collections/siklu/eh
	rm -rf ./collections/

# Full rebuild and test
rebuild: clean install test-all
