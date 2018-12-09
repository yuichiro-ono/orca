module CrossOrigin
  class Criteria < Mongoid::Criteria

    def initialize(criteria)
      criteria.instance_values.each { |name, value| instance_variable_set(:"@#{name}", value) }
    end

    def cross(origin = :default)
      origin = CrossOrigin.to_name(origin)
      cross_origin = CrossOrigin[origin]
      return unless cross_origin || origin == :default
      origins = Hash.new { |h, k| h[k] = [] }
      docs = []
      each do |record|
        unless record.origin == origin
          origins[record.collection] << record.id
          doc = record.attributes.dup
          doc['origin'] = origin
          docs << doc
        end
      end
      ((cross_origin && cross_origin.collection_for(klass)) || klass.collection).insert_many(docs) unless docs.empty?
      origins.each {|collection, ids| collection.find(_id: {'$in' => ids}).delete_many }
    end
  end
end