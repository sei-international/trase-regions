const fs = require("fs");
const path = require("path");
const mapshaper = require("mapshaper");
const childProcess = require("child_process");
const dataFolder = "./data";

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

const simplifyGeometries = (filePath, format, extension) => {
  console.log(`simplifying ${filePath}`);

  const fileName = path.basename(filePath);
  const folderPath = filePath.replace(fileName, "");

  try {
    mapshaper.runCommands(
      `-i ${filePath} -simplify visvalingam percentage=0.005 keep-shapes -o precision=0.00001 ${folderPath} target=* force format=${format} extension=${extension}`
    );
  } catch (error) {
    console.error(`Error simplifying ${filePath}: ${error.message}`);
  }
};

const geojsonFiles = readFiles(".geojson");
const topoJsonFiles = readFiles(".topo.json");

// geojsonFiles.forEach((filePath) =>
//   simplifyGeometries(filePath, "geojson", ".geojson")
// );

topoJsonFiles.forEach((filePath) =>
  simplifyGeometries(filePath, "topojson", ".json")
);
