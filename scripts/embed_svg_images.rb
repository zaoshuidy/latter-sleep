#!/usr/bin/env ruby

require "base64"

abort "usage: embed_svg_images.rb INPUT.svg OUTPUT.svg" unless ARGV.length == 2

input_path, output_path = ARGV
base_dir = File.dirname(File.expand_path(input_path))
svg = File.binread(input_path)

svg = svg.sub('width="309mm" height="216mm"', 'width="3650px" height="2551px"')
svg = svg.gsub(/(?:href|xlink:href)="([^"\n]+\.png)"/) do |attribute|
  relative_path = Regexp.last_match(1)
  image_path = File.expand_path(relative_path, base_dir)
  abort "missing embedded image: #{image_path}" unless File.file?(image_path)

  encoded = Base64.strict_encode64(File.binread(image_path))
  name = attribute.start_with?("xlink:") ? "xlink:href" : "href"
  %(#{name}="data:image/png;base64,#{encoded}")
end

File.binwrite(output_path, svg)
