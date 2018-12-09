require 'cross_origin/version'
require 'cross_origin/collection'
require 'cross_origin/document'
require 'cross_origin/criteria'

module CrossOrigin

  class << self

    def to_name(origin)
      if origin.is_a?(Symbol)
        origin
      else
        origin.to_s.to_sym
      end
    end

    def [](origin)
      origin_options[to_name(origin)]
    end

    def config(origin, options = {})
      origin = to_name(origin)
      fail "Not allowed for origin name: #{origin}" if origin == :default
      origin_options[origin] || (origin_options[origin] = Config.new(origin, options))
    end

    def configurations
      origin_options.values
    end

    def names
      origin_options.keys
    end

    private

    def origin_options
      @origin_options ||= {}
    end
  end

  private

  class Config

    attr_reader :name, :options

    def initialize(name, options)
      @name = name
      @options = options
    end

    def collection_name_for(model)
      "#{name}_#{model.mongoid_root_class.storage_options_defaults[:collection]}"
    end

    def collection_for(model)
      (Mongoid::Clients.clients[name] || Mongoid.default_client)[collection_name_for(model)]
    end
  end
end