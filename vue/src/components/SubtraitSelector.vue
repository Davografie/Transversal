<script setup lang="ts">
	import { ref, computed } from 'vue'
	import { useTraitset } from '@/composables/Traitset'
	// import { useTraitList } from '@/composables/TraitList'
	// import TraitsetSelector from './TraitsetSelector.vue'
	// import type { Traitset as TraitsetType } from '@/interfaces/Types'

	const props = defineProps<{
		traitset_id?: string,
		traitset_name?: string,
		selected_traits?: string[],
		selected_count?: number
	}>()

	const emit = defineEmits([
		'toggle_subtrait',
		'toggle_subtraitset'
	])

	const { traitset, retrieve_traitset, set_traitset_id } = useTraitset(undefined, props.traitset_id, undefined, undefined)
	// const { traits, retrieve_traits, set_traitset_id: set_traitlist_traitset_id } = useTraitList(undefined, props.traitset_id, undefined, undefined)

	
	const show_traits = ref(false)
	function toggle_show_traits() {
		show_traits.value = !show_traits.value
		if(show_traits.value) {
			retrieve_traitset()
		}
	}

	const trait_count = computed(() => props.selected_traits?.filter(x => traitset?.value.traits?.map(y => y.id).includes(x)).length)

	// function set_traitset(ts: TraitsetType) {
	// 	set_traitset_id(ts.id)
	// 	retrieve_traitset()
	// 	set_traitlist_traitset_id(ts.id)
	// 	retrieve_traits()
	// }

	// const trait = ref()

	// const alphabetical_traits = computed(() => {
	// 	return traits.value.sort((a, b) => a.name.localeCompare(b.name))
	// })
</script>

<template>
    <div class="traitset-selector" :class="{'sub-traitset': traitset?.entityTypes?.includes('subtrait')}">
		<!-- <TraitsetSelector @set_traitset="set_traitset" :initial_traitset_id="props.traitset_id" />
		<select v-model="trait">
			<option v-for="t in alphabetical_traits" :key="t.id" :value="t" @click="trait = t">
				{{ t.name }}
			</option>
		</select> -->
		<div class="header" @click="toggle_show_traits">
			<div class="amount">
				{{ props.selected_count ?? trait_count ?? 0 }}
			</div>
			<div class="traitset-name">
				{{ props.traitset_name ?? traitset?.name }}
			</div>
		</div>
		<div class="trait all" :class="{'selected': traitset.traits?.every(t => props.selected_traits?.includes(t.id))}"
				v-if="show_traits" @click="emit('toggle_subtraitset', traitset)">
			<div>select/deselect all traits below</div>
			<div>{{ traitset.traits?.every(t => props.selected_traits?.includes(t.id)) ? '✓' : 'x' }}</div>
		</div>
		<div class="trait" :class="{'selected': props.selected_traits?.includes(t.id)}"
				v-for="t in traitset.traits" :key="t.id"
				v-if="show_traits" @click="emit('toggle_subtrait', t)">
			<div>{{ t.name }}</div>
			<div>{{ props.selected_traits?.includes(t.id) ? '✓' : 'x' }}</div>
		</div>
    </div>
</template>

<style scoped>
.traitset-selector {
	.header {
		display: flex;
		cursor: pointer;
		.amount {
			width: 2em;
			text-align: center;
		}
		.traitset-name {
			flex-grow: 1;
			text-align: left;
		}
	}
	&.sub-traitset {
		.header .traitset-name {
			text-decoration: underline;
		}
	}
	.trait, .all {
		display: flex;
		justify-content: space-between;
		padding: 0 1em;
		cursor: pointer;
		&.selected {
			background-color: var(--color-highlight);
			color: var(--color-highlight-text);
		}
	}
	.all {
		text-shadow: none;
		padding: 0 2em;
	}
}
</style>
