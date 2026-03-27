<script setup lang="ts">
import { useDicepoolStore } from '@/stores/DicepoolStore';
import { useDicepool } from '@/composables/Dicepool';
import Die from '@/components/Die.vue';
const dicepoolStore = useDicepoolStore();
const dicepool = useDicepool(false);

const swade_result = {
	hitch: 'aw shit, a 1!',
	fail: 'no bueno, you fail',
	success: 'marginal success',
	average: 'average success',
	good: 'good success',
	excellent: 'excellent success'
}
</script>

<template>
	<div>
		<div id="swade-result-text">
			<div class="swade-result swade-hitch" v-if="dicepoolStore.dice[0].isHitch">
				<h1>aw shit, a 1!</h1>
				<div class="details">
					<span class="detail">
						result: <Die :die="dicepoolStore.dice[0]" in_pool />
					</span>
					<span class="detail">
						effect: <Die :die="{ number_rating: -2, rating: 'd6' }" />
					</span>
				</div>
			</div>
			<div class="swade-result swade-fail" v-else-if="dicepoolStore.dice[0].result < 3">
				<h1>no bueno, you fail</h1>
				<div class="details">
					<span class="detail">
						result: <Die :die="dicepoolStore.dice[0]" in_pool />
					</span>
					<span class="detail">
						effect: <Die :die="{ number_rating: -1, rating: 'd4' }" />
					</span>
				</div>
			</div>
			<div class="swade-result swade-success" v-else-if="dicepoolStore.dice[0].result < 6">
				<h1>marginal success</h1>
				<div class="details">
					<span class="detail">
						result: <Die :die="dicepoolStore.dice[0]" in_pool />
					</span>
					<span class="detail">
						effect: <Die :die="{ number_rating: 1, rating: 'd4' }" />
					</span>
				</div>
			</div>
			<div class="swade-result swade-raise" v-else-if="dicepoolStore.dice[0].result < 9">
				<h1>success!</h1>
				<div class="details">
					<span class="detail">
						result: <Die :die="dicepoolStore.dice[0]" in_pool />
					</span>
					<span class="detail">
						effect: <Die :die="{ number_rating: 2, rating: 'd6' }" />
					</span>
				</div>
			</div>
			<div class="swade-result swade-raise" v-else-if="dicepoolStore.dice[0].result < 12">
				<h1>Excellent!!</h1>
				<div class="details">
					<span class="detail">
						result: <Die :die="dicepoolStore.dice[0]" in_pool />
					</span>
					<span class="detail">
						effect: <Die :die="{ number_rating: 3, rating: 'd8' }" />
					</span>
				</div>
			</div>
			<div class="swade-result swade-raise" v-else-if="dicepoolStore.dice[0].result < 20">
				<h1>Fucking A!!!</h1>
				<div class="details">
					<span class="detail">
						result: <Die :die="dicepoolStore.dice[0]" in_pool />
					</span>
					<span class="detail">
						effect: <Die :die="{ number_rating: 4, rating: 'd10' }" />
					</span>
				</div>
			</div>
			<div class="swade-result swade-raise" v-else>
				<h1>GODLIKE</h1>
				<div class="details">
					<span class="detail">
						result: <Die :die="dicepoolStore.dice[0]" in_pool />
					</span>
					<span class="detail">
						effect: <Die :die="{ number_rating: 5, rating: 'd12' }" />
					</span>
				</div>
			</div>
			<div class="glowing">
				<span style="--i:1;"></span>
				<span style="--i:2;"></span>
				<span style="--i:3;"></span>
			</div>
			
			<div class="glowing">
				<span style="--i:1;"></span>
				<span style="--i:2;"></span>
				<span style="--i:3;"></span>
			</div>
			
			<div class="glowing">
				<span style="--i:1;"></span>
				<span style="--i:2;"></span>
				<span style="--i:3;"></span>
			</div>
			
			<div class="glowing">
				<span style="--i:1;"></span>
				<span style="--i:2;"></span>
				<span style="--i:3;"></span>
			</div>
		</div>
	</div>
</template>

<style scoped>
#swade-result-text {
			position: relative;
			overflow: hidden;
			margin: 10px;
			border: 1px solid var(--color-highlight);
			backdrop-filter: blur(5px);
			text-shadow: var(--text-shadow);
			.swade-result {
				display: flex;
				flex-direction: column;
				align-items: center;
				div.details {
					width: 100%;
					display: flex;
					justify-content: space-evenly;
					span.detail {
						display: flex;
						align-items: center;
					}
				}
			}
			/* https://alvarotrigo.com/blog/animated-backgrounds-css/ */
			.glowing {
				position: absolute;
				min-width: 700px;
				height: 550px;
				margin: -150px;
				transform-origin: right;
				animation: colorChange 5s linear infinite;
			}

			.glowing:nth-child(even) {
				transform-origin: left;
			}

			.glowing span {
				position: absolute;
				top: calc(80px * var(--i));
				left: calc(80px * var(--i));
				bottom: calc(80px * var(--i));
				right: calc(80px * var(--i));
			}

			.glowing span::before {
				content: "";
				position: absolute;
				top: 50%;
				left: -8px;
				width: 15px;
				height: 15px;
				background: #f00;
				border-radius: 50%;
			}

			.glowing span:nth-child(3n + 1)::before {
				background: rgba(134,255,0,1);
				box-shadow: 0 0 20px rgba(134,255,0,1),
					0 0 40px rgba(134,255,0,1),
					0 0 60px rgba(134,255,0,1),
					0 0 80px rgba(134,255,0,1),
					0 0 0 8px rgba(134,255,0,.1);
			}

			.glowing span:nth-child(3n + 2)::before {
				background: rgba(255,214,0,1);
				box-shadow: 0 0 20px rgba(255,214,0,1),
					0 0 40px rgba(255,214,0,1),
					0 0 60px rgba(255,214,0,1),
					0 0 80px rgba(255,214,0,1),
					0 0 0 8px rgba(255,214,0,.1);
			}

			.glowing span:nth-child(3n + 3)::before {
				background: rgba(0,226,255,1);
				box-shadow: 0 0 20px rgba(0,226,255,1),
					0 0 40px rgba(0,226,255,1),
					0 0 60px rgba(0,226,255,1),
					0 0 80px rgba(0,226,255,1),
					0 0 0 8px rgba(0,226,255,.1);
			}

			.glowing span:nth-child(3n + 1) {
				animation: animate 10s alternate infinite;
			}

			.glowing span:nth-child(3n + 2) {
				animation: animate-reverse 3s alternate infinite;
			}

			.glowing span:nth-child(3n + 3) {
				animation: animate 8s alternate infinite; 
			}
		}
</style>
