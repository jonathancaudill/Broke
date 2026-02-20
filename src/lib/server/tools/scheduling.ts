import { tool, jsonSchema } from 'ai';

export const checkAvailabilityTool = tool({
	description: "Check Jonathan's calendar availability for a given date range. Returns a list of open time slots.",
	inputSchema: jsonSchema<{ start_date: string; end_date: string }>({
		type: 'object',
		properties: {
			start_date: {
				type: 'string',
				description: 'Start of the date range (ISO 8601, e.g. 2026-02-20).'
			},
			end_date: {
				type: 'string',
				description: 'End of the date range (ISO 8601, e.g. 2026-02-27).'
			}
		},
		required: ['start_date', 'end_date']
	}),
	execute: async ({ start_date, end_date }) => {
		return (
			`[STUB] Available slots between ${start_date} and ${end_date}:\n` +
			'  - Mon 10:00–11:30 AM CST\n' +
			'  - Tue 2:00–4:00 PM CST\n' +
			'  - Thu 9:00–10:00 AM CST\n' +
			'  - Fri 1:00–3:00 PM CST\n\n' +
			'Note: this is placeholder data. Calendar integration is not yet wired up.'
		);
	}
});

export const bookMeetingTool = tool({
	description: 'Book a meeting with Jonathan at a specific time. Requires a time slot, the requester\'s name, and their email.',
	inputSchema: jsonSchema<{ datetime: string; name: string; email: string; topic?: string }>({
		type: 'object',
		properties: {
			datetime: {
				type: 'string',
				description: 'Requested meeting time (ISO 8601, e.g. 2026-02-24T14:00:00).'
			},
			name: {
				type: 'string',
				description: 'Name of the person requesting the meeting.'
			},
			email: {
				type: 'string',
				description: 'Contact email for the meeting requester.'
			},
			topic: {
				type: 'string',
				description: 'Brief topic or agenda for the meeting.'
			}
		},
		required: ['datetime', 'name', 'email']
	}),
	execute: async ({ datetime, name, email, topic }) => {
		return (
			`[STUB] Meeting request logged:\n` +
			`  Time:  ${datetime}\n` +
			`  With:  ${name} (${email})\n` +
			`  Topic: ${topic || 'not specified'}\n\n` +
			'Note: this is a scaffold. Calendar booking is not yet wired up — ' +
			'Jonathan has not actually been notified.'
		);
	}
});
