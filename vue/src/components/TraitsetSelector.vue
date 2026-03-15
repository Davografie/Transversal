<script setup lang="ts">
	import { ref, watch } from 'vue'
	import { useTraitsetList } from '@/composables/TraitsetList';
	import type { Traitset, Entity } from '@/interfaces/Types';
	const props = defineProps<{
		initial_traitset_id?: string
		entity_id?: string
		entity_type?: string,
		entity?: Entity
	}>()
	const emits = defineEmits(['set_traitset'])

	const {
		traitsets,
		retrieve_traitsets,
		retrieve_traitsets_by_type_and_location
	} = useTraitsetList(
		undefined,
		props.entity_id,
		props.entity_type ?? props.entity?.entityType,
		props.entity?.location?.id
	)

	retrieve_traitsets_by_type_and_location()

	const traitset = ref(traitsets.value.find((ts) => ts.id == props.initial_traitset_id) ?? {name: ''} as Traitset)

	watch(() => props.initial_traitset_id, () => {
		traitset.value = traitsets.value.find((ts) => ts.id == props.initial_traitset_id)
	})
</script>

<template>
	<div class="traitset-selector">
		<select v-model="traitset" @change="emits('set_traitset', traitset)">
			<option :value="{name: ''}">select traitset</option>
			<option v-for="ts in traitsets" :key="ts.id" :value="ts">
				{{ ts.name }}
			</option>
		</select>
	</div>
</template>

<style scoped>
</style>
