var camera, scene, renderer, controls;
var geometry, material, mesh;
var players, playerGeometry, entityMaterial, entities, entityGeometry;
var date = new Date();
var last_snapshot = date.getTime();
var left = false;
var right = false;
var up = false;
var space = false

var Entity = function (id, phys, material, geometry, scene) {
    this.id = id;
    this.pos = phys[0];
    this.vel = phys[1];
    this.size = phys[2];
    this.mesh = new THREE.Mesh(geometry, material);
    this.mesh.scale.set(this.size, this.size, this.size);
    scene.add(this.mesh);
}

Entity.prototype.update_phys = function (phys) {
    this.pos = phys[0];
    this.vel = phys[1];
    this.size = phys[2];
}

var Player = function (sid, phys, color, geometry, scene) {
    this.sid = sid;
    this.pos = phys[0]
    this.vel = phys[1];
    this.size = phys[2];
    this.dir = phys[3];
    this.color = parseInt(color);
    this.genMesh(geometry, scene);
    this.bullets = {};
}

Player.prototype.genMesh = function (geometry, scene) {
    this.material = new THREE.MeshBasicMaterial({ color: this.color });
    this.mesh = new THREE.Mesh(geometry, this.material);
    this.mesh.rotateX(Math.PI / 2);
    this.mesh.scale.set(scale, scale, scale);
    scene.add(this.mesh);
}

Player.prototype.update_phys = function (phys) {
    this.pos = phys[0]
    this.vel = phys[1];
    this.size = phys[2];
    if (socket.id != this.sid) {
        this.dir = phys[3];
    } 
}

function initGL() {
    scene = new THREE.Scene();
    var width = window.innerWidth;
    var height = window.innerHeight;
    if (width > height) {
        width = height;
    } else {
        height = width;
    }
    scale = height/40
    camera = new THREE.OrthographicCamera(0, width, height, 0, 1, 1000);
    camera.position.z = 100;
    scene.add(camera);

    var playerLoader = new THREE.JSONLoader();
    playerLoader.load('/static/models/player.json', function (geometry) {
        playerGeometry = geometry;
        initSocket();
    });

    entityMaterial = new THREE.MeshBasicMaterial({ color: 0xffffff });
    entityGeometry = new THREE.CircleGeometry(1, 6);

    players = {};
    entities = {};

    renderer = new THREE.WebGLRenderer();
    renderer.setSize(width, height);
    renderer.autoClear = false;

    composer = new THREE.EffectComposer(renderer);
    var renderpass = new THREE.RenderPass(scene, camera);
    var bloompass = new THREE.BloomPass(3, 25, 4, 256);
    composer.addPass(renderpass);
    composer.addPass(bloompass);




    var effectcopy = new THREE.ShaderPass(THREE.CopyShader);
    effectcopy.renderToScreen = true;
    composer.addPass(effectcopy);

    document.getElementById('draw').appendChild(renderer.domElement);
    clock = new THREE.Clock();
}

function initSocket() {
    socket = io();
    socket.on('game_snapshot', processSnapshot);
    socket.on('player_disconnect', function (sid) {
        scene.remove(players[sid].mesh);
        delete players[sid];
    });
    socket.on('bullet_expire', function (data) {
        scene.remove(players[data[0]].bullets[data[1]].mesh);
        delete players[data[0]].bullets[data[1]];
    })
    document.addEventListener('keydown', keydownListener);
    document.addEventListener('keyup', keyupListener);
    setInterval(move_update, 1000 / 60);
    setInterval(update_status, 1000 / 30);
    animate();
}

function keydownListener(event) {
    var keyCode = event.which;
    if (keyCode == 37 && !left) {
        left = true;
    } else if (keyCode == 39 && !right) {
        right = true;
    } else if (keyCode == 38 && !up) {
        up = true;
    } else if (keyCode == 32 && !space) {
        space = true;
    }
}

function keyupListener(event) {
    var keyCode = event.which;
    if (keyCode == 37) {
        left = false;
    } else if (keyCode == 39) {
        right = false;
    } else if (keyCode == 38) {
        up = false;
    } else if (keyCode == 32) {
        space = false;
    }
}

function processSnapshot(raw_data) {
    if (typeof self_player == "undefined") {
        self_player = players[socket.id]
    }
    data = JSON.parse(raw_data);
    date = new Date();
    last_snapshot = date.getTime();
    for (var i = 0; i < data.players.length; i++) {
        player_data = data.players[i]
        if (!(player_data.sid in players)) {
            players[player_data.sid] = new Player(player_data.sid, player_data.phys, player_data.color,playerGeometry, scene);
        } else {
            players[player_data.sid].update_phys(player_data.phys);
        }
        player = players[player_data.sid];
        for (var j = 0; j < player_data.bullets.length; j++) {
            bullet_data = player_data.bullets[j];
            if (!(bullet_data.id in player.bullets)) {
                player.bullets[bullet_data.id] = new Entity(bullet_data.id, bullet_data.phys, player.material, entityGeometry, scene);
            } else {
                player.bullets[bullet_data.id].update_phys(bullet_data.phys);
            }
        }
    }

    for (var i = 0; i < data.entities.length; i++) {
        entity_data = data.entities[i]
        if (!(entity_data.id in entities)) {
            entities[entity_data.id] = new Entity(entity_data.id, entity_data.phys, entityMaterial, entityGeometry, scene);
        } else {
            entities[entity_data.id].update_phys(entity_data.phys);
        }
    }
}

function animate() {
    requestAnimationFrame(animate);
    date = new Date();
    var delta_time = date.getTime() - last_snapshot;
    var delta_ticks = delta_time / (1000 / 20);
    //console.log(delta_time);
    for (var sid in players) {
        if (!players.hasOwnProperty(sid)) continue;

        var player = players[sid];
        player.mesh.position.set((player.pos[0] + player.vel[0] * delta_ticks)*scale, (player.pos[1] + player.vel[1] * delta_ticks)*scale, 0);
        player.mesh.rotation.y = player.dir;

        for (var id in player.bullets) {
            if (!player.bullets.hasOwnProperty(id)) continue;

            var bullet = player.bullets[id];
            bullet.mesh.position.set((bullet.pos[0] + bullet.vel[0] * delta_ticks) * scale, (bullet.pos[1] + bullet.vel[1] * delta_ticks) * scale, 0);
        }
    }

    for (var id in entities) {
        if (!entities.hasOwnProperty(id)) continue;

        var entity = entities[id];
        entity.mesh.position.set((entity.pos[0] + entity.vel[0] * delta_ticks) * scale + Math.random()*2 - 1, (entity.pos[1] + entity.vel[1] * delta_ticks) * scale + Math.random()*2 - 1, 0);
    }
    var delta = clock.getDelta();
    renderer.clear();
    composer.render(delta);
    //renderer.render(scene, camera);
}

function move_update() {
    if (typeof self_player != "undefined") {
        if (left) {
            self_player.dir += Math.PI / 100;
        }
        if (right) {
            self_player.dir -= Math.PI / 100;
        }
    }
}

function update_status() {
    if (typeof self_player != "undefined") {
        socket.emit('player_update', [self_player.dir, up, space]);
    }    
}

initGL();