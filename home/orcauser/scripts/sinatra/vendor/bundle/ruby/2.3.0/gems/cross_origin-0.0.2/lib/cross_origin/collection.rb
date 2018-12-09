module CrossOrigin
  class Collection < Mongo::Collection

    attr_reader :default_collection, :model

    def initialize(default_collection, model)
      default_collection.instance_values.each { |name, value| instance_variable_set(:"@#{name}", value) }
      @default_collection = default_collection
      @model = model
    end

    def find(filter = nil, options = {})
      View.new(self, filter || {}, options, model)
    end

    class View < Mongo::Collection::View

      attr_reader :model

      def initialize(collection, selector, options, model)
        super(collection, selector, options)
        @model = model
      end

      def each(&block)
        if block
          super(&block)
          cross_views.each { |view| view.each(&block) }
        end
      end

      def count(options = {})
        super + (options[:super] ? 0 : cross_views.inject(0) { |count, view| count + view.count })
      end

      def cross_views
        views = []
        skip, limit = self.skip, self.limit
        opts = options
        previous_view = self
        count = 0
        CrossOrigin.configurations.each do |config|
          if skip || limit
            opts = opts.dup
            current_count = previous_view.count(super: true)
            if skip
              opts[:skip] = skip =
                if current_count < skip
                  skip - current_count
                else
                  count += current_count - skip
                  0
                end
            end
            if limit
              opts[:limit] = limit =
                if count > limit
                  0
                else
                  limit - count
                end
            end
          end
          views << (previous_view = config.collection_for(model).find(selector, opts).modifiers(modifiers))
        end
        views
      end

      def new(options)
        View.new(collection, selector, options, model)
      end
    end
  end
end