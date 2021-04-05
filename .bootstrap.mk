# Export all Make variables by default to sub-make as well as Shell calls.
#
# Note that you can still explicitely mark a variable with `unexport` and it is
# not going to be exported by Make, regardless of this setting.
#
# https://www.gnu.org/software/make/manual/html_node/Variables_002fRecursion.html
export

# Disable/enable various make features.
#
# https://www.gnu.org/software/make/manual/html_node/Options-Summary.html
MAKEFLAGS += --no-builtin-rules
MAKEFLAGS += --no-builtin-variables
MAKEFLAGS += --no-print-directory
MAKEFLAGS += --warn-undefined-variables

# Set `help` as the default goal to be used if no targets were specified on the command line
#
# https://www.gnu.org/software/make/manual/html_node/Special-Variables.html
.DEFAULT_GOAL:=help

# Never delete a target if it exits with an error.
#
# https://www.gnu.org/software/make/manual/html_node/Special-Targets.html
.DELETE_ON_ERROR:

# Disable the suffix functionality of make.
#
# https://www.gnu.org/software/make/manual/html_node/Suffix-Rules.html
.SUFFIXES:

# This executes all targets in a single shell. This improves performance, by
# not spawning a new shell for each line, and also allows use to write multiline
# commands like conditions and loops without escaping sequences.
#
# https://www.gnu.org/software/make/manual/html_node/One-Shell.html
.ONESHELL:

# This makes all targets silent by default, unless VERBOSE is set.
ifndef VERBOSE
.SILENT:
endif

# The shell that should be used to execute the recipes.
SHELL       := bash
.SHELLFLAGS := -euo pipefail -c

# Determine the root directory of our codebase and export it, this allows easy
# file inclusion in both Bash and Make.
override ROOT := $(shell path="$(CURDIR)"; while [[ "$${path}" != "/" \
 && ! -f "$${path}/.bootstrap.mk" ]]; do path="$${path%/*}"; done; echo "$${path}")

## Built-in

# A generic help message that parses the available targets, and lists each one
# that has a comment on the same line with a ## prefix.
help: ## Display this help
	readonly pad=$$(printf "%0.1s" "_"{1..25}); \
	print_targets() { \
		local -n targets_ref=$$1; \
		if (( "$${#targets_ref[@]}" > 0 )); then \
			declare -a keys=(); \
			readarray -t keys < <(printf "%s\n" "$${!targets_ref[@]}" | sort -d); \
			for target in "$${keys[@]}"; do \
				printf "%s\n" "$${targets_ref[$$target]}"; \
			done; \
		fi; \
	}; \
	targets() { \
		declare -A targets=(); \
		local target_pattern='[^:]+::?[^#]*## +.*'; \
		local section_pattern='^## .*'; \
		for mk in "$$@"; do \
			while read -r line; do \
				if [[ "$${line}" =~ $${section_pattern} ]]; then \
					print_targets targets; \
					targets=(); \
					local comment="$${line##*## }"; \
					printf "  \033[1m%s\033[0m\n" "$${comment}"; \
				elif [[ "$${line}" =~ $${target_pattern} ]]; then \
					local target="$${line%%:*}"; \
					local comment="$${line##*## }"; \
					if [ "$${targets[$${target}]+x}" ]; then \
						targets["$${target}"]+=$$(printf "\n    %$${#pad}s  %s\n" "" "$${comment}"); \
					else \
						targets["$${target}"]=$$(printf "    \033[0;32m%s\033[0m \033[0;90m%s\033[0m %s\n" "$${target}" "$${pad:$${#target}}" "$${comment}"); \
					fi; \
				fi; \
			done < "$${mk}"; \
			print_targets targets; \
			targets=(); \
		done; \
	}; \
	print_option() { \
		printf "    \033[0;32m%s\033[0m \033[0;90m%s\033[0m %s \033[0;33m[default: %s]\033[0m\n\n" "$$1" "$${pad:$${#1}}" "$$2" "$$3"; \
	}; \
	echo; \
	echo -e "\033[0;33mUsage:\033[0m"; \
	echo -e "    make [flags...] [target...] [options...]"; \
	echo; \
	echo -e "\033[0;33mFlags:\033[0m"; \
	echo -e "    See; \033[1mmake --help\033[0m" \
	echo; \
	echo -e "\033[0;33mTargets:\033[0m"; \
	targets $(MAKEFILE_LIST); \
	echo -e "\n\033[0;33mOptions:\033[0m"; \
	print_option 'VERBOSE=<mode>' 'Set mode to 1 for verbose output' '0'
.PHONY: help

# Target to update make-bootstrap once installed
self-update: ## Update make-bootstrap
	echo "backing up existing bootstrap file..."
	cp .bootstrap.mk ".bootstrap.mk.$(shell date +%s)"
	echo "downloading latest version from github.com/dsiebel/make-bootstrap (master)"
	curl --location --retry 3 --show-error --silent --output .bootstrap.mk \
	 "https://raw.githubusercontent.com/dsiebel/make-bootstrap/master/.bootstrap.mk"
	 echo "done!"
.PHONY: self-update
