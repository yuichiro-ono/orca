# Cross Origin

With cross origin you can store and retrieve documents with your Mongoid models from multiples collections.

## Installation

Add this line to your application's Gemfile:

```ruby
gem 'cross_origin'
```

And then execute:

    $ bundle

Or install it yourself as:

    $ gem install cross_origin

## Usage

Configurate your origins

```ruby
CrossOrigin.config :test
```

and include the module `CrossOrigin::Document` in your Mongoid class. Then use the `cross` method on records or criterias to send records to an origin collection.


## Development

After checking out the repo, run `bin/setup` to install dependencies. Then, run `bin/console` for an interactive prompt that will allow you to experiment.

To install this gem onto your local machine, run `bundle exec rake install`. To release a new version, update the version number in `version.rb`, and then run `bundle exec rake release` to create a git tag for the version, push git commits and tags, and push the `.gem` file to [rubygems.org](https://rubygems.org).

## Contributing

1. Fork it ( https://github.com/macarci/cross_origin/fork )
2. Create your feature branch (`git checkout -b my-new-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin my-new-feature`)
5. Create a new Pull Request
