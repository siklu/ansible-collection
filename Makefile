.PHONY: help install build clean test-unit test-integration test-rollback test-all rebuild

help:
	@echo "Siklu EH Ansible Collection - Available targets:"
	@echo "  make install            - Build and install collection"
	@echo "  make build              - Build collection tarball"
	@echo "  make clean              - Remove build artifacts"
	@echo "  make test-unit          - Run unit tests (pytest)"
	@echo "  make test-integration   - Run integration tests (facts)"
	@echo "  make test-rollback      - Run rollback integration tests"
	@echo "  make test-all           - Run all tests"
	@echo "  make rebuild            - Clean, install, and test"

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

# Run rollback integration tests
test-rollback:
	@echo "Running rollback protection integration tests..."
	ansible-playbook test_rollback.yaml -i inventory.ini -v

# Run all tests
test-all: test-unit test-integration test-rollback
	@echo "All tests completed!"

# Clean build artifacts
clean:
	rm -f siklu-eh-*.tar.gz
	rm -rf ~/.ansible/collections/ansible_collections/siklu/eh
	rm -rf ./collections/

# Full rebuild and test
rebuild: clean install test-all
