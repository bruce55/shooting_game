/// <reference path="three.d.ts"/>

declare class Player {
    mesh: THREE.Mesh;
}

declare var players: { [sid: string]: Player }