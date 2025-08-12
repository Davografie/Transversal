<script setup lang="ts">
	const props = defineProps<{
		truthy: string,
		falsy: string,
		default: boolean
	}>()
</script>

<template>
	<div class="toggle-button">
		<input
			type="button"
			class="button-mnml"
			id="truthy-button"
			:value="props.truthy"
			:class="props.default ? 'active' : 'inactive'"
			@click="$emit('toggle')" />
		<input
			type="button"
			class="button-mnml"
			id="falsy-button"
			:value="props.falsy"
			:class="!props.default ? 'active' : 'inactive'"
			@click="$emit('toggle')" />
	</div>
</template>

<style scoped>
	.toggle-button {
		max-width: 100%;
		display: flex;
		justify-content: center;
		.button-mnml {
			flex-grow: 1;
			&.active {
				padding: .4em 2em;
				box-shadow: 0 0 20px var(--color-highlight);
				background-color: var(--color-highlight);
				color: var(--color-highlight-text);
				border-color: var(--color-highlight);
				font-weight: bold;
			}
			&.inactive {
				padding: .4em 1em;
			}
		}
		&:hover {
			.active {
				padding: .4em 1em;
			}
			.inactive {
				padding: .4em 2em;
				box-shadow: 0 0 20px var(--color-highlight);
			}
		}
	}
	#truthy-button {
		border-radius: 20px 0 0 0;
		&.inactive {
			background-image: linear-gradient(to left, var(--color-border) 0%, var(--color-background) 20%);
		}
	}
	#falsy-button {
		border-radius: 0 0 20px 0;
		&.inactive {
			background-image: linear-gradient(to right, var(--color-border) 0%, var(--color-background) 20%);
		}
	}
</style>
