// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// https://astro.build/config
export default defineConfig({
	integrations: [
		starlight({
			title: 'Gilial Documentation',
			description: 'Compress your vector database intelligently',
			social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/aadyantmaity/Gilial' }],
			sidebar: [
				{
					label: 'Getting Started',
					items: [
						{ label: 'Introduction', slug: 'getting-started/introduction' },
						{ label: 'Installation', slug: 'getting-started/installation' },
						{ label: 'Quick Start', slug: 'getting-started/quick-start' },
					],
				},
				{
					label: 'Guides',
					items: [
						{ label: 'Compression Strategies', slug: 'guides/strategies' },
						{ label: 'Using Dry-Run Mode', slug: 'guides/dry-run' },
						{ label: 'Best Practices', slug: 'guides/best-practices' },
					],
				},
				{
					label: 'API Reference',
					items: [
						{ label: 'REST API', slug: 'api/rest-api' },
					],
				},
			],
		}),
	],
});
