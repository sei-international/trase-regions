const fs = require("fs");
const path = require("path");
const mapshaper = require("mapshaper");

const DATA_FOLDER = "./data";
const MAX_FILE_SIZE_MB = 6.5;

function findFilesByExtension(fileExtension) {
  const files = [];

  function walkDirectory(dir) {
    const entries = fs.readdirSync(dir);

    entries.forEach((entry) => {
      const fullPath = path.join(dir, entry);
      const isDirectory = fs.statSync(fullPath).isDirectory();

      if (isDirectory) {
        walkDirectory(fullPath);
      } else if (entry.endsWith(fileExtension)) {
        files.push(fullPath);
      }
    });
  }

  walkDirectory(DATA_FOLDER);
  return files;
}

const getFileSizeInMB = (filePath) => {
  const stats = fs.statSync(filePath);
  const fileSizeInBytes = stats.size;
  return fileSizeInBytes / 1_000_000;
};

const simplifyGeometriesIfTooLarge = async (filePath, format, extension) => {
  // Checks if files are larger than MAX_FILE_SIZE_MB, if yes, simplifies them
  // using mapshaper until they're under that limit.
  const currentSize = getFileSizeInMB(filePath);

  if (currentSize < MAX_FILE_SIZE_MB) {
    console.log(
      `✅ ${filePath} is already under the size limit of ${MAX_FILE_SIZE_MB} MB, skipping`
    );
    return;
  }

  console.log(`🔄 Simplifying ${filePath} (${currentSize.toFixed(2)} MB)...`);

  const fileName = path.basename(filePath);
  const folderPath = filePath.replace(fileName, "");

  try {
    await mapshaper.runCommands(
      `-i ${filePath} -simplify visvalingam percentage=0.01 keep-shapes -snap -o precision=0.00001 ${folderPath} target=* force format=${format} extension=${extension}`
    );
  } catch (error) {
    console.error(`Error simplifying ${filePath}: ${error.message}`);
  }

  const newSize = getFileSizeInMB(filePath);
  if (newSize > MAX_FILE_SIZE_MB) {
    console.log(
      `⚠️  ${filePath} still too large (${newSize.toFixed(
        2
      )} MB) - needs re-run`
    );
    // run again
    simplifyGeometriesIfTooLarge(filePath, format, extension);
  } else {
    console.log(
      `✅ simplified ${filePath} to ${newSize.toFixed(
        2
      )} megabytes, which is under the limit`
    );
  }
};

const geojsonFiles = findFilesByExtension(".geojson");

geojsonFiles.forEach((filePath) =>
  simplifyGeometriesIfTooLarge(filePath, "geojson", ".geojson")
);
