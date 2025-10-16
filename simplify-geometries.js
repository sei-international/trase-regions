const fs = require("fs");
const path = require("path");
const mapshaper = require("mapshaper");
const childProcess = require("child_process");
const dataFolder = "./data";

const MAX_FILE_SIZE_MB = 6.5;

const readFiles = (fileExtension) => {
  const files = [];
  const walkSync = (dir, fileList) => {
    const list = fs.readdirSync(dir);
    fileList = fileList || [];
    list.forEach((file) => {
      if (fs.statSync(path.join(dir, file)).isDirectory()) {
        fileList = walkSync(path.join(dir, file), fileList);
      } else {
        if (file.endsWith(fileExtension)) {
          fileList.push(path.join(dir, file));
        }
      }
    });
    return fileList;
  };
  return walkSync(dataFolder, files);
};

const getFileSizeInMB = (filePath) => {
  const stats = fs.statSync(filePath);
  const fileSizeInBytes = stats.size;
  return fileSizeInBytes / 1000000.0;
}

const simplifyGeometries = async (filePath, format, extension) => {
  if (getFileSizeInMB(filePath) < MAX_FILE_SIZE_MB) {
    return;
  }

  console.log(`simplifying ${filePath}`);

  const fileName = path.basename(filePath);
  const folderPath = filePath.replace(fileName, "");

  try {
    await mapshaper.runCommands(
      `-i ${filePath} -simplify visvalingam percentage=0.01 keep-shapes -snap -clean -o precision=0.00001 ${folderPath} target=* force format=${format} extension=${extension}`
    );
  } catch (error) {
    console.error(`Error simplifying ${filePath}: ${error.message}`);
  }

  const s = getFileSizeInMB(filePath);
  if (s > MAX_FILE_SIZE_MB) {
    console.log(`⚠️ ${filePath} is still too large and this script needs to be re-run (${s} megabytes for a limit of ${fileSizeInMegabytes} megabytes`);
  } else {
    console.log(`✅ simplified ${filePath} to ${s} megabytes, which is under the limit`);
  }
};

const geojsonFiles = readFiles(".geojson");
const topoJsonFiles = readFiles(".topo.json");

geojsonFiles.forEach((filePath) =>
  simplifyGeometries(filePath, "geojson", ".geojson")
);

topoJsonFiles.forEach((filePath) =>
  simplifyGeometries(filePath, "topojson", ".json")
);
