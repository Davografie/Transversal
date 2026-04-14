<script setup lang="ts">
import { ref, computed } from 'vue'
import { useTraitset } from '@/composables/Traitset'
import type { Trait } from '@/interfaces/Types'

const props = defineProps<{
	traitset_id: string,
	subtraits: Trait[]
}>()

const emits = defineEmits<{
	click_subtrait: [subtrait: Trait]
}>()

const sorted_traits = computed(() => {
	return props.subtraits.sort((a, b) => {
		return a.name.localeCompare(b.name)
	}).sort((a, b) => {
		return (b.randomWeight ?? 0) - (a.randomWeight ?? 0)
	})
})

const { traitset, retrieve_traitset } = useTraitset(undefined, props.traitset_id, undefined, undefined)
retrieve_traitset()

const random_subtrait = ref<Trait>()
function assign_random() {
	let subtrait_list = []
	// make sure the randomizer takes the randomWeight into account
	// e.g. a subtrait with randomWeight 4 should have twice the chance of being picked than a subtrait with randomWeight 2
	for(const subtrait of props.subtraits) {
		if(subtrait.randomWeight) {
			// add subtraits equal to the amount of randomWeight to the subtrait_list
			for(let i = 0; i < subtrait.randomWeight; i++) {
				subtrait_list.push(subtrait)
			}
		}
	}
	// random_subtrait.value = props.subtraits[Math.floor(Math.random() * props.subtraits.length)]
	random_subtrait.value = subtrait_list[Math.floor(Math.random() * subtrait_list.length)]
}
</script>

<template>
	<div class="subtraitset-assign" v-if="props.subtraits.length > 0">
		<div class="traitset-info">
			{{ traitset.name }}
		</div>
		<div class="subtraits">
			<div class="subtrait button-mnml random" v-if="props.subtraits.length > 1" @click="assign_random">
				random 🎲
			</div>
			<div class="subtrait button-mnml" v-for="subtrait in sorted_traits" :key="subtrait.id"
					:class="{ 'random-pick': random_subtrait?.id == subtrait.id }"
					@click="emits('click_subtrait', subtrait)">
				{{ subtrait.name }}
			</div>
		</div>
	</div>
</template>

<style scoped>
.subtraitset-assign {
	.subtrait {
		display: inline-block;
		&.random {
			border-right: 1px solid var(--color-text);
		}
		&.random-pick {
			background-color: var(--color-highlight);
			color: var(--color-highlight-text);
		}
	}
}
</style>
