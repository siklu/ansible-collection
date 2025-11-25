.PHONY: help install build clean test-unit test-integration test-all rebuild

help:
	@echo "Siklu EH Ansible Collection - Available targets:"
	@echo "  make install           - Build and install collection"
	@echo "  make build             - Build collection tarball"
	@echo "  make clean             - Remove build artifacts"
	@echo "  make test-unit         - Run unit tests (pytest)"
	@echo "  make test-integration  - Run integration tests (Ansible)"
	@echo "  make test-all          - Run all tests"
	@echo "  make rebuild           - Clean, install, and test"

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

# Run integration tests
test-integration:
	@echo "Running integration tests..."
	ansible-playbook test_facts.yaml -i inventory.ini -v

# Run all tests
test-all: test-unit test-integration
	@echo "All tests completed!"

# Clean build artifacts
clean:
	rm -f siklu-eh-*.tar.gz
	rm -rf ~/.ansible/collections/ansible_collections/siklu/eh
	rm -rf ./collections/

# Full rebuild and test
rebuild: clean install test-all
