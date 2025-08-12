<script setup lang="ts">
	import PoolTrait from './PoolTrait.vue'
	import { useDicepool } from '@/composables/Dicepool'
	import { useTraitset } from '@/composables/Traitset'
	import type { Die } from '@/interfaces/Types'
	const props = defineProps<{
		traitset_id: string
		dice: Die[]
	}>()
	const emit = defineEmits(['longpress_die'])

	const dicepool = useDicepool()
	const { traitset, retrieve_traitset } = useTraitset(undefined, props.traitset_id)
	retrieve_traitset()
	function remove_trait(traitsetting_id: string) {
		if(dicepool.inAddingPhase.value) dicepool.remove_traitsetting_dice(traitsetting_id)
	}
</script>

<template>
	<div class="pool-traitset-wrapper pool-wrapper">
		{{  traitset.name }}
		<template v-for="traitsetting in new Set(props.dice.map((d) => d.traitsettingId ?? 'custom')).values()" :key="traitsetting">
			<PoolTrait v-if="traitsetting"
				:traitsetting_id="traitsetting"
				:dice="props.dice.filter((d) => d.traitsettingId ?? 'custom' == traitsetting)"
				@click="remove_trait(traitsetting)"
				@longpress_die="(die: Die) => emit('longpress_die', die)" />
		</template>
	</div>
</template>

<style scoped>
	.pool-wrapper {
		padding-left: 1em;
	}
	.pool-traitset-wrapper {
		padding: .4em 1em;
	}
</style>
