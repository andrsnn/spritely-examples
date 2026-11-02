#!/bin/bash
# Downloads the 9 free CC0 KayKit characters (made by Kay Lousberg, kaylousberg.com) into ./characters.
set -e
mkdir -p characters && cd characters
B=https://raw.githubusercontent.com/KayKit-Game-Assets
for c in Barbarian Knight Mage Rogue Rogue_Hooded; do
  curl -sfL -o $c.glb $B/KayKit-Character-Pack-Adventures-1.0/main/addons/kaykit_character_pack_adventures/Characters/gltf/$c.glb
done
for c in Skeleton_Mage Skeleton_Minion Skeleton_Rogue Skeleton_Warrior; do
  curl -sfL -o $c.glb $B/KayKit-Character-Pack-Skeletons-1.0/main/addons/kaykit_character_pack_skeletons/Characters/gltf/$c.glb
done
ls -la
