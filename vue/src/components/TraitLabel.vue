<script setup lang="ts">
	import { computed } from 'vue';
	import { useTrait } from '@/composables/Trait'
	import { useDicepool } from '@/composables/Dicepool';
	import { die_constants } from '@/composables/Die';

	const props = defineProps<{
		trait_setting_id: string
	}>()

	const { trait, retrieve_trait } = useTrait(undefined, undefined, props.trait_setting_id)
	retrieve_trait()

	const dicepool = useDicepool()
	const dice_in_pool = computed(() => dicepool.trait_dice(props.trait_setting_id))
</script>

<template>
	<div class="trait-label" :class="trait.ratingType != 'empty' ? die_constants.find(dc => dc.number_rating == Math.max(...(trait.rating?.map(die => Math.abs(die.number_rating)) ?? [0])))?.rating : ''">
		{{ trait.statement || trait.name }}
		<span v-for="d of dice_in_pool" :key="d.id">
			{{ d.number_rating > 0 ?
				die_constants.find(dc => d.number_rating == dc.number_rating)?.active
				: die_constants.find(dc => d.number_rating == dc.number_rating)?.inactive }}
		</span>
	</div>
</template>

<style scoped>
	.trait-label {
		font-size: .8em;
		border: 1px solid var(--color-border);
		border-radius: 10px;
		padding: 0 .4em;
		background-color: var(--color-background-soft);
		&.d4 {
			background-color: var(--color-positive-die-4);
			color: var(--color-positive-die-4-text);
		}
		&.d6 {
			background-color: var(--color-positive-die-6);
			color: var(--color-positive-die-6-text);
		}
		&.d8 {
			background-color: var(--color-positive-die-8);
			color: var(--color-positive-die-8-text);
		}
		&.d10 {
			background-color: var(--color-positive-die-10);
			color: var(--color-positive-die-10-text);
		}
		&.d12 {
			background-color: var(--color-positive-die-12);
			color: var(--color-positive-die-12-text);
		}
	}
</style>
