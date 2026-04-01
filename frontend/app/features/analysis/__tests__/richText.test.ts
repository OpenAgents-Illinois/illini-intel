import { splitIntoParagraphs } from "../components/richText";

test("splitIntoParagraphs preserves explicit paragraph breaks", () => {
  expect(splitIntoParagraphs("First paragraph.\n\nSecond paragraph.")).toEqual([
    "First paragraph.",
    "Second paragraph.",
  ]);
});

test("splitIntoParagraphs chunks wall-of-text into readable paragraphs", () => {
  expect(
    splitIntoParagraphs(
      "Illinois can score in bunches. UConn will test the glass. Transition defense matters. Bench usage could swing the second half.",
    ),
  ).toEqual([
    "Illinois can score in bunches. UConn will test the glass.",
    "Transition defense matters. Bench usage could swing the second half.",
  ]);
});
