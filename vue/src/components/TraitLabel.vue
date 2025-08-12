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
	<div class="trait-label">
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
	}
</style>
