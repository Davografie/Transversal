<script setup lang="ts">
	import { watch, defineProps } from 'vue';
	import { useTraitList } from '@/composables/TraitList';
	import Trait from '@/components/Trait.vue';

	const props = defineProps<{
		entity_id: string;
	}>();

	const {
		traits,
		retrieve_entity_traits
	} = useTraitList(undefined, undefined, props.entity_id, false);

	retrieve_entity_traits();

	watch(() => props.entity_id, () => {
		retrieve_entity_traits();
	});
</script>

<template>
	<div class="all-traits">
		<Trait v-for="trait in traits" :key="trait.traitSetting?.id"
			:trait_setting_id="trait.traitSetting?.id"
			:entity_id="props.entity_id"
			:trait_id="trait.id"
			/>
	</div>
</template>

<style scoped>
	.all-traits {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
	}
</style>
