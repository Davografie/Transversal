<script setup lang="ts">
	import Die from '@/components/Die.vue'
	import type { Die as DieType } from '@/interfaces/Types'
	import { useTrait } from '@/composables/Trait'

	const props = defineProps<{
		traitsetting_id: string,
		dice: DieType[]
		entity_id?: string,
	}>()

	const emit = defineEmits([
		'click_die',
		'click_complication'
	])

	const { trait, retrieve_trait } = useTrait(undefined, undefined, props.traitsetting_id, props.entity_id)
	retrieve_trait()
</script>

<template>
	<div class="suggested-trait">
		<div class="trait-description" @click="emit('click_complication')">
			<div class="trait-name">
				{{ trait.name }}
			</div>
			<div class="trait-statement" v-if="trait.traitSetting?.statement">
				{{ trait.traitSetting?.statement }}
			</div>
		</div>
		<div class="trait-rating">
			<Die v-for="die in props.dice.filter((d) => d.traitsettingId == props.traitsetting_id)" :die="die" @click.stop="emit('click_die', die)" />
		</div>
	</div>
</template>

<style scoped>
.suggested-trait {
	display: flex;
	/* justify-content: space-between; */
	align-items: center;
	gap: 1em;
	.trait-description {
		.trait-name {
			font-weight: bold;
		}
		.trait-statement {
			font-style: italic;
		}
	}
	.trait-rating {
		max-height: 2.4em;
		display: flex;
		gap: .4em;
	}
}
</style>
