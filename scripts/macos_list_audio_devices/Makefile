CC = clang
FRAMEWORKS = -framework Foundation -framework CoreAudio
SOURCE_FILE = list_audio_devices.m
OUTPUT_DIR = build
OUTPUT_FILE = $(OUTPUT_DIR)/list_audio_devices

# Default target
all: $(OUTPUT_FILE)

# Create output directory
$(OUTPUT_DIR):
	mkdir -p $(OUTPUT_DIR)

# Compile and link
$(OUTPUT_FILE): $(OUTPUT_DIR)
	$(CC) $(FRAMEWORKS) $(SOURCE_FILE) -o $(OUTPUT_FILE)

# Clean
clean:
	rm -rf $(OUTPUT_DIR)

# Run
run: $(OUTPUT_FILE)
	$(OUTPUT_FILE)
