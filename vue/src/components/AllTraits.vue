<script setup lang="ts">
	import { watch, onMounted } from 'vue';
	import { useTraitList } from '@/composables/TraitList';
	import Trait from '@/components/Trait.vue';

	const props = defineProps<{
		entity_id: string;
	}>();

	const {
		traits,
		retrieve_entity_traits,
		set_entity_id
	} = useTraitList(undefined, undefined, props.entity_id, false);

	onMounted(() => {
		retrieve_entity_traits();
	});

	watch(() => props.entity_id, (newId) => {
		set_entity_id(newId);
		retrieve_entity_traits();
	});
</script>

<template>
	<div class="all-traits">
		<Trait class="trait" v-for="trait in traits" :key="trait.traitSetting?.id"
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
		/* flex-direction: column; */
		gap: 8px;
		max-height: calc(100vh - 32em);
		overflow: auto;
		.trait {
			max-width: 18em;
		}
	}
</style>
