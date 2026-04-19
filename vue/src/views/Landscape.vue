<script setup lang="ts">
	import { ref, computed, watch } from 'vue';
	import { useRoute } from 'vue-router';
	import { useWindowSize } from '@vueuse/core'

	import { usePlayerStore } from '@/stores/PlayerStore';

	import CharacterView from '@/views/CharacterView.vue';
	import CurrentLocationView from '@/views/CurrentLocationView.vue';
	import CodexView from '@/views/CodexView.vue';
	import DicepoolView from '@/views/DicepoolView.vue';
	import SettingsView from '@/views/SettingsView.vue';

	import type { Location as LocationType } from '@/interfaces/Types';
	import DicepoolFloater from '@/components/DicepoolFloater.vue';

	const emits = defineEmits([
		'engage',
		'next_beat'
	])

	const route = useRoute()
	const player = usePlayerStore()

	const { width: windowWidth, height: windowHeight } = useWindowSize()
	const third_width = computed(() => windowWidth.value / 3)

	const dicepool_expanded = ref(false)

	function expand_dicepool() {
		dicepool_expanded.value = true
		emits('engage')
	}

	//	changed by show_entity()
	const active_entity_id = ref<string|undefined>()

	function show_entity(entity_id: string) {
		if(active_entity_id.value != entity_id) {
			active_entity_id.value = entity_id
		}
		else {
			active_entity_id.value = undefined
		}
	}
	
	watch(route, () => {
		active_entity_id.value = undefined
	})
</script>

<template>
	<div id="landscape-container">

		<div id="panels" v-if="route.matched.length < 2 || route.matched[1].name != 'Settings'">
			<CharacterView
				class="panel character-panel"
				v-if="player.the_entity"
				:entity_key="player.the_entity?.key"
				orientation="horizontal"
				@show_entity="show_entity" />
			<CurrentLocationView id="current-location" class="panel"
				:location_key="player.the_entity?.location?.key ?? ''"
				@show_entity="show_entity"
				:active_entity_id="active_entity_id"
				v-if="player.the_entity?.location" />
			<CodexView id="codex" class="panel"
				@show_entity="show_entity"
				shown />
		</div>

		<div id="settings-container" v-if="route.matched.length > 1 && route.matched[1].name == 'Settings'">
			<SettingsView
				orientation="horizontal"
				@show_entity="show_entity" />
		</div>

		<DicepoolFloater @engage="emits('engage')" />


		<footer id="landscape-footer">
			<DicepoolView id="dicepool" ref="dicepool"
				:expanded="dicepool_expanded"
				@expand="expand_dicepool"
				@collapse="dicepool_expanded = false"
				@next_beat="emits('next_beat')" />
		</footer>
	</div>
</template>

<style scoped>
	header {
		z-index: 10;
		font-size: 1.4em;
		width: 100vw;
		height: v-bind(header_height + 'px');
		text-align: center;
		position: fixed;
		a {
			background-color: transparent;
			color: var(--color-text);
			padding: 0;
		}
		nav {
			display: flex;
			justify-content: space-evenly;
			line-height: 1.2em;
		}
		#character, #perspective {
			background-color: var(--color-highlight);
			color: var(--color-highlight-text);
			border-radius: 0 0 30px 30px / 0 0 15px 15px;
			height: 2em;
			text-align: center;
			padding: 0 1em;
			line-height: 2em;
		}
	}
	#edit-button, #floating-buttons {
		right: 34%;
	}
	#panels {
		display: grid;
		/* grid-template-columns: v-bind(third_width + 'px') v-bind(third_width + 'px') v-bind(third_width + 'px'); */
		grid-template-columns: minmax(24em, 2fr) 4fr 130px;
		width: 100vw;
		height: 100vh;
		.character-panel {
			background-image: linear-gradient(to left, var(--color-background-mute) 0, transparent 20px);
		}
	}
	.panel {
		/* padding-top: v-bind(header_height + 'px'); */
		/* margin-bottom: 10em; */
		height: 100vh;
		/* width: v-bind(third_width + 'px'); */
		overflow-x: hidden;
		/* overflow-y: auto; */
	}
	/* #content {
		height: 100vh;
	} */
	#dicepool-container {
		position: fixed;
		bottom: 0;
		display: flex;
		justify-content: center;
		height: 0;
		width: 100vw;
		overflow: visible;
		z-index: 10;
		#dicepool {
			position: absolute;
			bottom: -1px;
		}
	}
</style>

<style></style>
