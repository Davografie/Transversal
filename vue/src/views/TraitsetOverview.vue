<script setup lang="ts">
	import { ref, type Ref, watch } from 'vue'
	import { usePlayerStore } from '@/stores/PlayerStore'
	import { useTraitsetList } from '@/composables/TraitsetList'

	const emit = defineEmits(['show_traitset'])

	const player = usePlayerStore()

	const {
		traitsets,
		create_traitset,
		retrieve_traitsets,
		change_traitset_order
	} = useTraitsetList(undefined, undefined, undefined)

	retrieve_traitsets()

	// filled by the DOM?
	const entity_types: Ref<Array<string>> = ref([])

	const traitset_order = ref<string[]>([])
	watch(traitsets, () => {
		traitset_order.value = traitsets.value.map((ts) => ts.id)
	})

	const order_changed = ref(false)
	const changed_index = ref(0)
	function order_change(event: any) {
		const { oldIndex, newIndex } = event
		order_changed.value = true
		let ts = traitset_order.value.splice(oldIndex, 1)[0]
		traitset_order.value.splice(newIndex, 0, ts)
		changed_index.value = newIndex
	}
	function save_order() {
		change_traitset_order(traitset_order.value)
		order_changed.value = false
	}

	const new_traitset: Ref<string> = ref('')
	function add_traitset() {
		create_traitset(new_traitset.value, entity_types.value)
		new_traitset.value = ''
		// entity_types.value = []
	}
</script>

<template>
	<div id="traitsets-wrapper">
		<h1>Traitsets</h1>
		<div id="create-traitset" v-if="player.is_gm">
			<input type="text" placeholder="new traitset" v-model="new_traitset" />
			<div id="entity-types">
				<div class="entity-type">
					<input type="checkbox" id="character" value="character" v-model="entity_types" />
					<label for="character">Characters</label>
				</div>
				<div class="entity-type">
					<input type="checkbox" id="faction" value="faction" v-model="entity_types" />
					<label for="faction">Factions</label>
				</div>
				<div class="entity-type">
					<input type="checkbox" id="npc" value="npc" v-model="entity_types" />
					<label for="npc">NPCs</label>
				</div>
				<div class="entity-type">
					<input type="checkbox" id="asset" value="asset" v-model="entity_types" />
					<label for="asset">Assets</label>
				</div>
				<div class="entity-type">
					<input type="checkbox" id="location" value="location" v-model="entity_types" />
					<label for="location">Locations</label>
				</div>
				<div class="entity-type">
					<input type="checkbox" id="relation" value="relation" v-model="entity_types" />
					<label for="relation">Relations</label>
				</div>
				<div class="entity-type">
					<input type="checkbox" id="subtrait" value="subtrait" v-model="entity_types" />
					<label for="subtrait">Subtraits</label>
				</div>
				<div class="entity-type">
					<input type="checkbox" id="gm" value="gm" v-model="entity_types" />
					<label for="gm">GM</label>
				</div>
			</div>
			<input type="button" class="button" value="create" v-if="new_traitset" @click="add_traitset" />
		</div>
		<div id="traitset-list">
			<div id="traitset-list-wrapper">
				<ol v-sortable @update="order_change">
					<li v-for="traitset in traitsets.filter(
								ts => entity_types.every(
									et => ts.entityTypes?.includes(et)))
								.filter(ts => ts.name?.toLowerCase().includes(new_traitset.toLowerCase()))"
							@click="emit('show_traitset', traitset.key)"
							:class="[
								{ 'subtraitset': traitset.entityTypes?.includes('subtrait') },
								{ 'emphasized': traitsets.filter(
								ts => entity_types.every(
									et => ts.entityTypes?.includes(et)))
								.filter(ts => ts.name?.toLowerCase().includes(new_traitset.toLowerCase())).includes(traitset) },
								{ 'changed': changed_index == traitset_order.indexOf(traitset.id) }
							]">
						<span>{{ traitset.name }}</span>
					</li>
					<!-- <li v-for="traitset in traitsets"
							@click="emit('show_traitset', traitset.key)"
							:class="[
								{ 'subtraitset': traitset.entityTypes?.includes('subtrait') },
								{ 'emphasized': traitsets.filter(
								ts => entity_types.every(
									et => ts.entityTypes?.includes(et)))
								.filter(ts => ts.name?.toLowerCase().includes(new_traitset.toLowerCase())).includes(traitset) },
								{ 'changed': changed_index == traitset_order.indexOf(traitset.id) }
							]">
						<span>{{ traitset.name }}</span>
					</li> -->
				</ol>
			</div>
			<div id="save-button-wrapper">
				<input type="button" id="save-button" class="button" value="save order" @click="save_order" v-if="order_changed" />
			</div>
		</div>
		<div class="bottom-scroll-space"></div>
	</div>
</template>

<style scope>
#traitsets-wrapper {
	#traitset-list {
		position: relative;
		/* background-color: var(--color-background-soft); */
		background: repeating-linear-gradient(0deg, 
			var(--color-background-soft),
			var(--color-background-soft) 4px,
			var(--color-background) 4px,
			var(--color-background) 8px);
		li {
			margin: 2px;
			text-align: center;
			border: 1px solid var(--color-border);
			font-size: 1.2em;
			padding: .2em;
			cursor: grab;
			/* &.subtraitset span {
				background-color: var(--color-highlight);
				color: var(--color-highlight-text);
			} */
			&.emphasized span {
				background-color: var(--color-highlight);
				color: var(--color-highlight-text);
				font-size: 1.4em;
			}
			&.changed {
				background-color: var(--color-editing);
				color: var(--color-editing-text);
			}
			&:hover {
				background-color: var(--color-highlight);
				color: var(--color-highlight-text);
			}
		}
		#traitset-list-wrapper {
			width: 60%;
			border: 3px double var(--color-border);
			background-color: var(--color-background);
			max-height: 100%;
		}
		#save-button-wrapper {
			position: absolute;
			top: 0;
			right: 0;
			height: 100%;
			width: 0;
			overflow: visible;
			#save-button {
				position: absolute;
				top: 0;
				right: 0;
				/* transform: translateY(-50%); */
			}
		}
	}
	.bottom-scroll-space {
		height: 100px;
	}
}
</style>

<style>
.dark {
	#traitsets-wrapper {
		h1, #entity-types {
			text-shadow: var(--text-shadow);
		}
		/* backdrop-filter: blur(5px); */
	}
}
.landscape {
	#traitsets-wrapper {
		padding-top: 4em;
	}
}
</style>
