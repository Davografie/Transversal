<script setup lang="ts">
import { usePlayer } from '@/stores/Player';
import { useSession } from '@/composables/Session'
import { ref, watch } from 'vue';
const { new_session, next_scene, next_beat } = useSession()
const player = usePlayer()
const changing_beat = ref(false)
function next_something(what: string) {
	if(changing_beat.value) {
		return
	}
	changing_beat.value = true
	if(what === 'session') {
		new_session()
	}
	if(what === 'scene') {
		next_scene()
	}
	if(what === 'beat') {
		next_beat()
	}
}
watch(() => player.beat_id, () => {
	if(changing_beat.value) {
		changing_beat.value = false
	}
})
</script>

<template>
	<div id="session-control" :class="{ 'changing-beat': changing_beat }">
		<input type="button" class="button-mnml" id="new-session" value="new session" @click="next_something('session')" />
		<input type="button" class="button-mnml" id="new-scene" value="next scene" @click="next_something('scene')" />
		<input type="button" class="button-mnml" id="new-beat" value="next beat" @click="next_something('beat')" />
	</div>
</template>

<style scoped>
#session-control {
	display: flex;
	justify-content: center;
	gap: 1px;
	padding: .4em;
	.button-mnml {
		flex-grow: 1;
		height: 3em;
		background-color: var(--color-background);
		border: 1px solid var(--color-border);
	}
	&.changing-beat {
		opacity: 0.5;
		.button-mnml {
			cursor: not-allowed;
		}
	}
}
</style>
