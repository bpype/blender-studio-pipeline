 # /./././././././././././././././././././././././././././././././
 # SETTINGS
 # /./././././././././././././././././././././././././././././././

 NAME = brushstroke_tools
 VERSION = v0.0.0
 BUILD_DIR = ./
 BUILD_FILE = $(BUILD_DIR)/$(NAME)_$(VERSION).zip
 FILES = *.py icons/* assets/* LICENSE blender_manifest.toml
 FILE_BROWSER = nautilus

 .DEFAULT_GOAL := build

 # /./././././././././././././././././././././././././././././././
 # TARGETS
 # /./././././././././././././././././././././././././././././././

clean:
	rm -rf $(BUILD_FILE)
	@echo "Release zip deleted - " $(BUILD_FILE)
build:
	mkdir -p $(BUILD_DIR)
	zip -r9T $(BUILD_FILE) $(FILES)
	@echo
	@echo $(NAME)" "$(VERSION) " is ready"
	$(FILE_BROWSER) $(BUILD_DIR) &
