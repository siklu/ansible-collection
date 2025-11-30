.PHONY: help install build clean test-unit test test-all rebuild

help:
	@echo "Siklu EH Ansible Collection - Available targets:"
	@echo "  make install       - Build and install collection"
	@echo "  make build         - Build collection tarball"
	@echo "  make clean         - Remove build artifacts"
	@echo "  make test-unit     - Run all unit tests (pytest)"
	@echo "  make test          - Run integration tests"
	@echo "  make test-all      - Run unit + integration tests"
	@echo "  make rebuild       - Clean, install, and test-all"

# Build collection
build:
	ansible-galaxy collection build --force

# Install collection
install: build
	ansible-galaxy collection install siklu-eh-*.tar.gz --force

# Run all unit tests
test-unit:
	@echo "Running all unit tests..."
	pytest tests/unit/ -v

# Run all integration tests
test:
	@echo "Running all integration tests..."
	ansible-playbook test_facts.yaml -i inventory.ini -v
	ansible-playbook test_command.yaml -i inventory.ini -v
	ansible-playbook test_config.yaml -i inventory.ini -v
	ansible-playbook test_set_commands.yaml -i inventory.ini -v
	ansible-playbook test_save_config.yaml -i inventory.ini -v
	ansible-playbook test_rollback.yaml -i inventory.ini -v
	@echo "All integration tests completed!"

# Run all tests (unit + integration)
test-all: test-unit test
	@echo "All tests completed!"

# Clean build artifacts
clean:
	rm -f siklu-eh-*.tar.gz
	rm -rf ~/.ansible/collections/ansible_collections/siklu/eh
	rm -rf ./collections/

# Full rebuild and test
rebuild: clean install test-all
