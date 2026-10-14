// Deepwick sample: exercises the syntax roles in the palette spec.
import { readFileSync } from "node:fs";

export interface Greeter {
  greet(name: string): string;
}

export enum Mood {
  Calm = 1,
  Stormy,
}

const MAX_RETRIES = 3;
const GREETING_PATTERN = /^hello,\s+(\w+)!$/i;

/** A developer who says hello. */
export class Developer implements Greeter {
  constructor(private readonly name: string, public mood: Mood = Mood.Calm) {}

  greet(name: string): string {
    if (this.mood === Mood.Stormy && !GREETING_PATTERN.test(`hello, ${name}!`)) {
      throw new Error("no one to greet");
    }
    return `Hello, ${name}!\n\tFrom ${this.name}`;
  }
}

function firstOf<T>(items: readonly T[]): T | undefined {
  return items.length > 0 ? items[0] : undefined;
}

export function sayHello(greeter: Greeter, names: string[]): number {
  let count = 0;
  for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
    for (const name of names) {
      console.log(greeter.greet(name));
      count += 1;
    }
  }
  const config = JSON.parse(readFileSync("config.json", "utf8")) as { verbose?: boolean };
  return config.verbose ? count : firstOf([count, 0x2a]) ?? 0;
}
