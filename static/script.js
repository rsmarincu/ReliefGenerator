var scene = new THREE.Scene();
var camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 100000);
var exporter = new THREE.OBJExporter();

canvas = document.getElementById('mainCanvas');
context = canvas.getContext('webgl');


var renderer = new THREE.WebGLRenderer({
  alpha: true,
  canvas: canvas,
  context: context
});

renderer.setSize(window.innerWidth, window.innerHeight);
renderer.gammaOutput = true;
renderer.gammaFactor = 2;

var controls = new THREE.OrbitControls(camera, renderer.domElement);

var light = new THREE.DirectionalLight(0xffffff, 1.1);

light.castShadow = true;
light.position.set(0.5, 1000, 0.1);
scene.add(light);
camera.position.set(500, 500, 500);

document.getElementById('location').addEventListener('submit', function(e) {
  e.preventDefault();

  let loader = document.getElementById('loader');
  let location = document.getElementById('textBox').value;
  let gridSize = document.querySelector('input[name="size"]:checked').value;
  let gridDistance = document.querySelector('input[name="distance"]:checked').value;

  loader.style.visibility='visible';

  for (let i = scene.children.length - 1; i >= 0; i--) {
    if (scene.children[i].type === "Mesh")
      scene.remove(scene.children[i]);
  }

  

  fetch('/hello', {
      method: 'POST',
      headers: {
        'Accept': 'application/json, text/plain, */*',
        'Content-type': 'application/json'
      },
      body: JSON.stringify({
        location: location,
        size: gridSize,
        distance: gridDistance
      })
    })
    .then((res) => res.json())
    .then(function(json) {
      
      var vertices = [];
      var holes = [];
      json.coordinate.forEach(function(coord) {
        var vert = new THREE.Vector3(coord.lat, coord.elev - json.lowest, coord.long);
        vertices.push(vert);
      });

      var size = json.size
      var length = size * size
      var triangles, mesh;
      var geometry = new THREE.Geometry();
      var material = new THREE.MeshPhongMaterial({
        color: 738827,
        specular: 0x009900,
        shininess: 2,
        flatShading: true
      });


      geometry.vertices = vertices;

      for (var i = 0; i < length - size; i++) {
        if ((i + 1) % size == 0) {
          continue;
        }
        geometry.faces.push(new THREE.Face3(i, i + 1, i + size));
      }
      for (var i = length; i > size; i--) {
        if (i % size == 0) {
          continue;
        }
        geometry.faces.push(new THREE.Face3(i, i - 1, i - size));
      }

      mesh = new THREE.Mesh(geometry, material);
      mesh.material.side = THREE.DoubleSide;

      let move = json.distance * json.size;
      mesh.position.x = -move / 2;
      mesh.position.z = -move / 2;
      camera.position.set(move,json.highest,move);
      mesh.name = 'relief';
      scene.add(mesh);
      camera.lookAt(mesh);
      controls.autoRotate = true;
      loader.style.visibility='hidden';

    });
    
});


function createSphere(lat, long, elev) {
  var geo = new THREE.SphereGeometry(10, 8, 8);
  var sphere = new THREE.Mesh(geo, materialSphere);
  sphere.position.x = lat;
  sphere.position.y = long;
  sphere.position.z = elev;
  scene.add(sphere);
  console.log('sphere added');
};

var downloadButton = document.getElementById('download-button');

downloadButton.addEventListener('click', function(){
  var mesh = scene.getObjectByName('relief');
  var objData = exporter.parse(mesh);
  console.log(objData);
  var blob = new Blob([objData], {type: "text/plain"});
  saveAs(blob,'relief.obj');
});

var animate = function() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
};

animate();
