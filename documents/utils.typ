#let mono-font = ("New Computer Modern Mono", "Source Han Sans SC")

#let prompt-counter = counter("prompt-counter")

#let ai-get(prompt, result) = context {
  prompt-counter.step()
  underline(
    stroke: teal.transparentize(60%) + 2pt,
    offset: 2pt,
    evade: false,
  )[
    #set text(font: mono-font)
    #text(fill: luma(190))[[#context prompt-counter.display()]] Prompt
  ]
  prompt
  linebreak()
  underline(
    stroke: orange.transparentize(60%) + 2pt,
    offset: 2pt,
    evade: false,
  )[
    #set text(font: mono-font)
    #text(fill: luma(190))[[#context prompt-counter.display()]] Result
  ]
  result
}
