import { tool } from 'ai';
import { z } from 'zod';

export const checkAvailabilityTool = tool({
	description: "Check Jonathan's calendar availability for a given date range. Returns a list of open time slots.",
	parameters: z.object({
		start_date: z.string().describe('Start of the date range (ISO 8601, e.g. 2026-02-20).'),
		end_date: z.string().describe('End of the date range (ISO 8601, e.g. 2026-02-27).')
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
	parameters: z.object({
		datetime: z.string().describe('Requested meeting time (ISO 8601, e.g. 2026-02-24T14:00:00).'),
		name: z.string().describe('Name of the person requesting the meeting.'),
		email: z.string().describe('Contact email for the meeting requester.'),
		topic: z.string().optional().describe('Brief topic or agenda for the meeting.')
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
